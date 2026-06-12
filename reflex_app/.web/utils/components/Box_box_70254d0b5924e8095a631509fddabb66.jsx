
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_70254d0b5924e8095a631509fddabb66 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_8bc3d2615708c6d209cd647bb7f35585 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.close_reconcile", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "24px", ["color"] : "#606088", ["cursor"] : "pointer", ["lineHeight"] : "1", ["&:hover"] : ({ ["color"] : "#FFFFFF" }), ["padding"] : "4px 6px" }),onClick:on_click_8bc3d2615708c6d209cd647bb7f35585},children)
    )
});
