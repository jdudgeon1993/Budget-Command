
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_49e5293125a7a5732539a0d497a966b6 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_12ec703b4078a42db5cdee326834ddda = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.toggle_create_cat", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 10px", ["borderRadius"] : "8px", ["border"] : "1px solid #252535", ["background"] : "#1c1c25", ["cursor"] : "pointer", ["flexShrink"] : "0", ["&:hover"] : ({ ["borderColor"] : "#3c3c56" }) }),onClick:on_click_12ec703b4078a42db5cdee326834ddda},children)
    )
});
