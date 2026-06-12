
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_263acb1311f659c089281750bcacedb0 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_8956e1e0622b3ffcc11ed47b06886255 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.delete_from_edit_tx", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "1", ["padding"] : "9px", ["borderRadius"] : "8px", ["border"] : "1px solid #f8717144", ["color"] : "#f87171", ["fontSize"] : "11px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.06em", ["&:hover"] : ({ ["background"] : "#f8717111" }) }),onClick:on_click_8956e1e0622b3ffcc11ed47b06886255},children)
    )
});
